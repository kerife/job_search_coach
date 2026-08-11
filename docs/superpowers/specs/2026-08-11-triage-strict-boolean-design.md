# Strict Boolean Semantics for Triage Delivery Contracts

## Context

The triage JSON schema declares immutable delivery and handoff flags as JSON
booleans. The Python validator currently compares values with Python's `!=`,
where `0 == False` and `1 == True`. A malformed triage packet can therefore
pass the runtime validator while the dependency-free schema checker rejects it.

## Design

Keep the schema and public behavior unchanged. In the triage validator, compare
each immutable expected value with strict JSON/Python type equality for:

- `delivery.draft_only` and `delivery.external_actions_authorized`;
- `handoff.auto_start`; and
- `handoff.reentry_packet.manual_reentry_required`,
  `raw_answer_retained`, and `external_actions_authorized`.

Canonical `true`/`false` values remain accepted. Numeric `0`/`1` values are
rejected with the existing bounded immutable-value diagnostics, without echoing
the supplied value. No schema, renderer, copy, privacy, or marketplace
manifest changes are required.

## Verification

TDD regression tests mutate every listed field to the opposite JSON numeric
shape and assert a non-zero validator result. Existing canonical triage,
schema-conformance, renderer, privacy, static, and release gates must remain
green.
