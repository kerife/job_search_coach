# Required provenance identifiers for case records

## Context

The case contract defines stable identifiers for every source, claim,
intervention, and outcome record. The validator currently checks those fields
only when supplied, so a record without its provenance handle can pass and
cannot be linked audibly downstream.

## Design

Require each record's declared provenance identifier to be present and to be a
non-empty string. Missing identifiers receive a deterministic path-specific
validation error; non-string or blank identifiers keep the existing type error.
Synthetic test fixtures will use stable IDs. The validator will not generate,
repair, or infer identifiers.

## Non-goals

No schema version, record shape, candidate binding, benchmark semantics, or
renderer behavior changes. Existing valid records with identifiers remain
byte-for-byte compatible.

## Acceptance

1. A source, claim, intervention, or outcome without its required ID is
   rejected with an error naming the exact array path and field.
2. Empty, non-string, and valid non-empty string ID behavior remains covered.
3. Focused case-validator, plugin, privacy, static, release, and installed
   smoke checks pass with source/cache parity preserved.
