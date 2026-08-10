# Strict question-rank validation

## Goal

Make the recruiter-practice semantic validator agree with the already strict
JSON Schema: the JSON numeric value equal to `1` is accepted for
`handoff_context.question_rank`, while JSON booleans must fail closed. JSON
Schema treats `1` and `1.0` as numerically equal; Python's `True == 1` is the
specific mismatch being removed.

## Scope and behavior

- Change only the practice-session validator comparison and its focused tests.
- Preserve the schema's `const: 1`, canonical integer `1`, all other handoff
  fields, copy, rendering order, privacy, and marketplace structure.
- Return the existing deterministic `question_rank must be 1` error without
  echoing the invalid value.
- Test `True` and `False` as rejected, numeric `1` and `1.0` as accepted, and
  schema/custom parity for each mutation.

## Verification

TDD requires a RED mutation against the current validator, then the minimal
type-safe comparison and GREEN focused tests. Run the practice contract,
schema-conformance, plugin-local, static, and final release gates before
publishing once through the existing cachebuster workflow.
