# Case Provenance ID Uniqueness Design

## Context

The case contract requires stable provenance IDs on every source, claim,
intervention, and outcome record. The validator currently checks presence and
type, but accepts two records in the same collection with the same ID. That
allows ambiguous attribution even when the records disagree on their other
fields.

## Decision

Require each provenance ID to be unique within its own collection:

- `sources[*].source_id`
- `claims[*].claim_id`
- `interventions[*].intervention_id`
- `outcomes[*].outcome_id`

Uniqueness is scoped per collection, so an ID may still appear in different
collections when those collections use different ID namespaces. The existing
required/non-empty-string check runs first; only a valid non-empty string is
added to the collection's `seen_ids` set. Duplicate errors identify the
record path and field but never echo the supplied ID value.

## Behavior and compatibility

Valid cases remain unchanged. Cases with duplicate IDs are rejected with a
deterministic path-specific error such as
`claims[1].claim_id must be unique`. Candidate binding, benchmark consent,
closed mappings, privacy checks, and all existing error wording remain
unchanged. No schema version change is needed because this tightens the
already-documented provenance contract at validation time.

## Verification

The regression matrix mutates a valid case for each collection, repeats the
first ID on a second otherwise-valid record, and asserts rejection at index 1
without echoing the ID. Existing validator, plugin, privacy, static, release,
and installed-cache smoke gates must remain green before publication.
